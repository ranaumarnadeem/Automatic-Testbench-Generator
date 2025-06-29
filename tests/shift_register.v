module shift_register (
    input clk,
    input rst,
    input din,
    output reg [7:0] dout
);
    always @(posedge clk or posedge rst) begin
        if (rst)
            dout <= 8'b0;
        else
            dout <= {dout[6:0], din};
    end
endmodule


// ---- Auto-generated testbench ----
`timescale 1ns/1ps
module shift_register_tb;
// Declare inputs and outputs
    reg clk;
    reg rst;
    reg din;
    wire [7:0] dout;

// Instantiate DUT
    shift_register uut (
        .clk(clk),
        .rst(rst),
        .din(din),
        .dout(dout)
    );

// Clock generation
    initial clk = 0;
    always #5 clk = ~clk;

initial begin
    rst = 1; #10; rst = 0;
        #10 din = 0;
        #10 din = 1;
        $finish;
end
endmodule