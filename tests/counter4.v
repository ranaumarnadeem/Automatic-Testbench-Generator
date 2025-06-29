module counter4 (
    input clk,
    input rst,
    input [3:0] en,
    output reg [3:0] out
);
    always @(posedge clk or posedge rst) begin
        if (rst)
            out <= 0;
        else if (|en)  // <-- fixed: scalar condition
            out <= out + 1;
    end
endmodule


// ---- Auto-generated testbench ----
`timescale 1ns/1ps
module counter4_tb;
    // regs for inputs, wires for outputs
    reg clk;
    reg rst;
  reg [3:0] en;
  wire [3:0] out;

    counter4 uut (
        .clk(clk),
        .rst(rst),
        .en(en),
        .out(out)
    );

    // Clock generation
    initial clk = 0;
    always #5 clk = ~clk;

    // Reset sequence
    initial begin
        rst = 1; #10; rst = 0;
    end

    initial begin
        en = 0;
        #10;
        en = 0;
        #10;
        en = 1;
        #10;
        en = 2;
        #10;
        en = 3;
        #10;
        en = 4;
        #10;
        en = 5;
        #10;
        en = 6;
        #10;
        en = 7;
        #10;
        en = 8;
        #10;
        en = 9;
        #10;
        en = 10;
        #10;
        en = 11;
        #10;
        en = 12;
        #10;
        en = 13;
        #10;
        en = 14;
        #10;
        en = 15;
        #10;
        $finish;
    end
endmodule