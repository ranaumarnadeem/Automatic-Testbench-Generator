module regfile #(
    parameter WIDTH = 8,
    parameter DEPTH = 4
)(
    input clk,
    input rst,
    input [1:0] wr_addr,
    input [WIDTH-1:0] wr_data,
    input wr_en,

    input [1:0] rd_addr[1:0],
    output reg [WIDTH-1:0] rd_data[1:0]
);

    reg [WIDTH-1:0] mem [DEPTH-1:0];
    integer i;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            for (i = 0; i < DEPTH; i = i + 1)
                mem[i] <= 0;
        end else begin
            if (wr_en)
                mem[wr_addr] <= wr_data;
        end
    end

    always @(*) begin
        rd_data[0] = mem[rd_addr[0]];
        rd_data[1] = mem[rd_addr[1]];
    end

endmodule



// ---- Auto-generated testbench ----
`timescale 1ns/1ps
module regfile_tb;
    // Declare regs for inputs and wires for outputs
    reg clk;
    reg rst;
    reg [1:0] wr_addr;
    reg wr_data;
    reg wr_en;
    reg [1:0] rd_addr;
    wire rd_data;

    // Instantiate the DUT
    regfile uut (
        .clk(clk),
        .rst(rst),
        .wr_addr(wr_addr),
        .wr_data(wr_data),
        .wr_en(wr_en),
        .rd_addr(rd_addr),
        .rd_data(rd_data)
    );

    // Clock generation
    initial clk = 0;
    always #5 clk = ~clk;

    // Reset sequence
    initial begin
        rst = 1;
        #10;
        rst = 0;
    end

    // Stimulus
    initial begin
        wr_addr = 0;
        wr_data = 0;
        wr_en = 0;
        rd_addr = 0;
        #10;
        // Example stimulus pattern
        integer i;
        for (i = 0; i < 4; i = i + 1) begin
            wr_addr = i % 4;
            wr_data = i % 2;
            wr_en = i % 2;
            rd_addr = i % 4;
            #10;
        end
        $finish;
    end
endmodule